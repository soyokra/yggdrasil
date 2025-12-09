# SQL模板注册

SQL模板注册，就是创建和添加MappedStatement

mybatis-plus会复用mybatis，将xxxMapper.xml文件定义的sql模板解析成MappedStatement。因此在xxxMapper.xml定义sql用法和mybatis一样

同时，mybatis-plus会执行自己的的方法，将预定义的selectList,insert,update,delete等方法，通过生成mybatis脚本的方式转成MappedStatement。 

mybatis-plus的Wrapper是mybatis的实体，mybatis会反射解析属性，对脚本动态内容进行判断和替换

脚本代码会转成sqlNode对象，脚本动态内容进行判断和替换的过程是转成sqlNode后执行的

```xml
<script>
    <if test="ew != null and ew.sqlFirst != null">
        ${ew.sqlFirst}
    </if> 

    SELECT 

    <choose>
        <when test="ew != null and ew.sqlSelect != null">
            ${ew.sqlSelect}
        </when>
        <otherwise>
            trade_id,created_at,updated_at
        </otherwise>
    </choose> 

    FROM trade 

    <if test="ew != null">
        <where>
            <if test="ew.entity != null">
                <if test="ew.entity['tradeId'] != null"> 
                    AND trade_id=#{ew.entity.tradeId}
                </if>
                <if test="ew.entity['createdAt'] != null"> 
                    AND created_at=#{ew.entity.createdAt}
                </if>
                <if test="ew.entity['updatedAt'] != null"> 
                    AND updated_at=#{ew.entity.updatedAt}
                </if>
            </if>

            <if test="ew.sqlSegment != null and ew.sqlSegment != '' and ew.nonEmptyOfWhere">
                <if test="ew.nonEmptyOfEntity and ew.nonEmptyOfNormal"> 
                    AND
                </if> 
                ${ew.sqlSegment}
            </if>
        </where>

        <if test="ew.sqlSegment != null and ew.sqlSegment != '' and ew.emptyOfWhere">
            ${ew.sqlSegment}
        </if>
    </if>  

    <if test="ew != null and ew.sqlComment != null">
        ${ew.sqlComment}
    </if>
</script>
```

## MybatisPlusAutoConfiguration

MybatisPlusAutoConfiguration的sqlSessionFactory()方法注册SqlSessionFactory类型的bean。是由MybatisSqlSessionFactoryBean进行处理的

```java
public class MybatisPlusAutoConfiguration implements InitializingBean {
    @Bean
    @ConditionalOnMissingBean
    public SqlSessionFactory sqlSessionFactory(DataSource dataSource) throws Exception {
        MybatisSqlSessionFactoryBean factory = new MybatisSqlSessionFactoryBean();
        return factory.getObject();
    }
}
```

## MybatisSqlSessionFactoryBean

MybatisSqlSessionFactoryBean 实际上构建sqlSessionFactory是通过afterPropertiesSet方法

```java
public class MybatisSqlSessionFactoryBean implements FactoryBean<SqlSessionFactory>, InitializingBean, ApplicationListener<ApplicationEvent> {
    public SqlSessionFactory getObject() throws Exception {
        if (this.sqlSessionFactory == null) {
            this.afterPropertiesSet();
        }

        return this.sqlSessionFactory;
    }

    public void afterPropertiesSet() throws Exception {
        Assert.notNull(this.dataSource, "Property 'dataSource' is required");
        Assert.state(this.configuration == null && this.configLocation == null || this.configuration == null || this.configLocation == null, "Property 'configuration' and 'configLocation' can not specified with together");
        SqlRunner.DEFAULT.close();
        this.sqlSessionFactory = this.buildSqlSessionFactory();
    }

    protected SqlSessionFactory buildSqlSessionFactory() throws Exception {
        // xml文件解析
        XMLMapperBuilder xmlMapperBuilder = new XMLMapperBuilder(mapperLocation.getInputStream(), (Configuration)targetConfiguration, mapperLocation.toString(), ((Configuration)targetConfiguration).getSqlFragments());
        xmlMapperBuilder.parse();

        //
    }


}
```

## XMLMapperBuilder

XMLMapperBuilder解析TradeMapper.xml，并将文件内的sql模板语句注册成MappedStatement

```java
public class XMLMapperBuilder extends BaseBuilder {
    public void parse() {
        if (!configuration.isResourceLoaded(resource)) {
            configurationElement(parser.evalNode("/mapper"));
            configuration.addLoadedResource(resource);
            bindMapperForNamespace();
        }
    }

    private void configurationElement(XNode context) {
        try {
            buildStatementFromContext(context.evalNodes("select|insert|update|delete"));
        } catch (Exception e) {
            throw new BuilderException("Error parsing Mapper XML. The XML location is '" + resource + "'. Cause: " + e, e);
        }
    }

    private void buildStatementFromContext(List<XNode> list, String requiredDatabaseId) {
        for (XNode context : list) {
            final XMLStatementBuilder statementParser = new XMLStatementBuilder(configuration, builderAssistant, context, requiredDatabaseId);
            try {
                statementParser.parseStatementNode();
            } catch (IncompleteElementException e) {
                configuration.addIncompleteStatement(statementParser);
            }
        }
    }

    public void parseStatementNode() {
        builderAssistant.addMappedStatement(id, sqlSource, statementType, sqlCommandType,
                fetchSize, timeout, parameterMap, parameterTypeClass, resultMap, resultTypeClass,
                resultSetTypeEnum, flushCache, useCache, resultOrdered,
                keyGenerator, keyProperty, keyColumn, databaseId, langDriver, resultSets);
    }
}
```

## MybatisConfiguration

XMLMapperBuilder 通过configuration，转到了MybatisConfiguration.addMapper() 方法

```java
public class XMLMapperBuilder extends BaseBuilder {
    private void bindMapperForNamespace() {
        configuration.addMapper(boundType);
    }
}

public class MybatisConfiguration extends Configuration {
    @Override
    public <T> void addMapper(Class<T> type) {
        mybatisMapperRegistry.addMapper(type);
    }
}
```

## MybatisMapperRegistry

```java
public class MybatisMapperRegistry extends MapperRegistry {
    @Override
    public <T> void addMapper(Class<T> type) {
        if (type.isInterface()) {
            boolean loadCompleted = false;
            try {
                // TODO 这里也换成 MybatisMapperProxyFactory 而不是 MapperProxyFactory
                knownMappers.put(type, new MybatisMapperProxyFactory<>(type));
                // TODO 这里也换成 MybatisMapperAnnotationBuilder 而不是 MapperAnnotationBuilder
                MybatisMapperAnnotationBuilder parser = new MybatisMapperAnnotationBuilder(config, type);
                parser.parse();
                loadCompleted = true;
            } finally {
                if (!loadCompleted) {
                    knownMappers.remove(type);
                }
            }
        }
    }
}
```

## MybatisMapperAnnotationBuilder

```java
public class MybatisMapperAnnotationBuilder extends MapperAnnotationBuilder {
    @Override
    public void parse() {
        String resource = type.toString();
        if (!configuration.isResourceLoaded(resource)) {
            try {
                // https://github.com/baomidou/mybatis-plus/issues/3038
                if (GlobalConfigUtils.isSupperMapperChildren(configuration, type)) {
                    parserInjector();
                }
            } catch (IncompleteElementException e) {
                configuration.addIncompleteMethod(new InjectorResolver(this));
            }
        }
        parsePendingMethods();
    }

    void parserInjector() {
        GlobalConfigUtils.getSqlInjector(configuration).inspectInject(assistant, type);
    }

}
```

## AbstractSqlInjector

```java
public abstract class AbstractSqlInjector implements ISqlInjector {
    @Override
    public void inspectInject(MapperBuilderAssistant builderAssistant, Class<?> mapperClass) {
        // 循环注入自定义方法
        methodList.forEach(m -> m.inject(builderAssistant, mapperClass, modelClass, tableInfo));
    }
}
```

## AbstractMethod

```java
public abstract class AbstractMethod implements Constants {
    public void inject(MapperBuilderAssistant builderAssistant, Class<?> mapperClass, Class<?> modelClass, TableInfo tableInfo) {
        injectMappedStatement(mapperClass, modelClass, tableInfo);
    }
}
```

## SelectList

```java
public class SelectList extends AbstractMethod {
    @Override
    public MappedStatement injectMappedStatement(Class<?> mapperClass, Class<?> modelClass, TableInfo tableInfo) {
        SqlMethod sqlMethod = SqlMethod.SELECT_LIST;
        String sql = String.format(sqlMethod.getSql(), sqlFirst(), sqlSelectColumns(tableInfo, true), tableInfo.getTableName(),
                sqlWhereEntityWrapper(true, tableInfo), sqlOrderBy(tableInfo), sqlComment());
        SqlSource sqlSource = languageDriver.createSqlSource(configuration, sql, modelClass);
        return this.addSelectMappedStatementForTable(mapperClass, getMethod(sqlMethod), sqlSource, tableInfo);
    }
}
```